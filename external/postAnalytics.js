var https = require('https');
var zlib = require('zlib');

var aws = require('aws-sdk');
var s3 = new aws.S3({ apiVersion: '2006-03-01' });

var LOG_REGEX = /^(.*?)\s(.*?)\s(\[.*?\])\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(\".*?\")\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(\".*?\")\s(\".*?\")\s(.*?)$/m;
var LOG_CF_REGEX = /^(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)$/m;

exports.handler = function(event, context) {
    console.log('Loading function');
    console.log('Node version', process.version);
    
    var record = event.Records[0];

    // Get the object from the event and show its content type
    var bucket = record.s3.bucket.name;
    var key = record.s3.object.key;

    console.log('Received new log: ' + bucket + '::' + key);

    var isS3Log = key.substr(0, 5) === 'logs/';
    var isCFLog = key.substr(0, 8) === 'logs-cf/';
    if (!isS3Log && !isCFLog) {
        context.succeed('Ignored non-log type: ' + key);
        return;
    }

    var wereInterestingLogs = false;

    function processS3Log(contentsRaw, cb) {
        var contents = contentsRaw.toString();
        var blobs = [];
        console.log('Processing ' + contents.length + 'byte log file...');
        contents.split(/\n/).forEach(function(line) {
            if (!line) return;
            var matches = LOG_REGEX.exec(line);
            if (!matches) {
                console.log('Unparsable line: ' + line);
                return;
            }

            var methodType = matches[7].split('.');
            // REST.*.OBJECT is an interesting log
            if (methodType[0] === 'REST' && methodType[2] === 'OBJECT') {
                wereInterestingLogs = true;
            }

            // console.log(matches);
            if (matches[7] !== 'REST.GET.OBJECT') {
                console.warn('Rejected, not REST.GET.OBJECT');
                return;
            }
            if (matches[10] !== '200') {
                if (matches[10] === '206') {
                    console.warn('206 partial content request not counted');
                } else {
                    console.warn('Rejected, not 200 response');
                }
                return;
            }
            if (matches[9].indexOf('?x-source=') === -1) {
                console.warn('Rejected, no source parameter');
                return;
            }
            if (matches[9].indexOf('&x-episode=') === -1) {
                console.warn('Rejected, no episode parameter');
                return;
            }

            // console.log(JSON.stringify(matches));
            blobs.push({
                userAgent: matches[17],
                ip: matches[4],
                source: /x-source=(\w+)/.exec(matches[9])[1],
                episode: /x-episode=([\w-]+)/.exec(matches[9])[1],
                ts: matches[3],
            });
        });

        cb(blobs);
    }

    function processCFLog(contentsRaw, cb) {
        console.log('Processing log from CloudFront...');
        console.log('Log size: ' + contentsRaw.length);
        try {
            zlib.gunzip(contentsRaw, function(err, res) {
                processCFLogDecompressed(err, res, cb);
            });
            console.log('Decompression started');
        } catch (e) {
            console.error(e);
            context.fail(e);
            return;
        }
    }
    function processCFLogDecompressed(err, contents, cb) {
        console.log('Results returned');
        if (err) {
            console.error('Problem during decompression');
            context.fail(err);
            return;
        }
        contents = contents.toString();
        console.log('Decompressed');
        var blobs = [];
        console.log('Processing ' + contents.length + 'byte log file...');
        contents.split(/\n/).forEach(function(line) {
            if (!line) return;
            if (line[0] === '#') return;

            var matches = LOG_CF_REGEX.exec(line);
            if (!matches) {
                console.log('Unparsable line: ' + line);
                return;
            }

            if (matches[6] !== 'GET') {
                console.warn('Rejected, not GET request');
                return;
            }
            if (matches[9] !== '200') {
                if (matches[9] === '206') {
                    console.warn('206 partial content request not counted');
                } else {
                    console.warn('Rejected, not 200 response: ' + matches[9]);
                }
                return;
            }
            wereInterestingLogs = true;
            if (matches[12].indexOf('x-source=') === -1) {
                console.warn('Rejected, no source parameter');
                return;
            }
            if (matches[12].indexOf('x-episode=') === -1) {
                console.warn('Rejected, no episode parameter');
                return;
            }

            // console.log(JSON.stringify(matches));
            blobs.push({
                userAgent: decodeURIComponent(matches[11]),
                ip: matches[5],
                source: /x-source=(\w+)/.exec(matches[12])[1],
                episode: /x-episode=([\w-]+)/.exec(matches[12])[1],
                ts: formatCFDate(matches[1], matches[2]),
            });
        });

        cb(blobs);
        return;

        function formatCFDate(date, time) {
            var dateSpl = date.split('-');
            var out = '[';
            out += dateSpl[2];
            out += '/';
            out += dateSpl[1];
            out += '/';
            out += dateSpl[0];
            out += ':';
            out += time;
            out += ' +0000]';

            return out;
        }
    }

    var params = {
        Bucket: bucket,
        Key: key,
    };
    s3.getObject(params, function(err, data) {
        if (err) {
            console.log('Error getting object ' + key + ' from bucket ' + bucket +
                '. Make sure they exist and your bucket is in the same region as this function.');
            context.fail('Error getting file: ' + err);
            return;
        }

        if (isS3Log) {
            processS3Log(data.Body, callback);
        } else if (isCFLog) {
            processCFLog(data.Body, callback);
        }

        function callback(blobs) {
            console.log('Num of logs: ' + blobs.length);
            if (!blobs.length) {
                context.succeed('Nothing to log');
                return;
            }

            var postData = 'payload=' + encodeURIComponent(JSON.stringify(blobs));
            blobs = null;

            console.log('Submitting ' + postData.length + 'byte payload');
            console.log(postData);
            var req = https.request(
                {
                    hostname: 'host.podmaster.io',
                    path: '/services/log?access=KEY_HERE',
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Content-Length': postData.length,
                    },
                },
                cleanUp
            );
            req.on('error', function(e) {
                context.fail(e);
            });
            req.write(postData);
            req.end();
        }

    });
    
    function cleanUp() {
        if (wereInterestingLogs) {
            console.log('Interesting logs were found, so no cleanup is needed.');
            context.succeed('Processing completed.');
        } else {
            console.log('Interesting logs were not found, so removing the log file.');
            s3.deleteObject(params, function(err) {
                if (err) {
                    console.error('Unexpected error cleaning up uninteresting log', err.toString());
                }
                context.succeed('Processing completed.');
            });
        }
    }
};
