console.log('Loading function');

var http = require('http');
var aws = require('aws-sdk');
var s3 = new aws.S3({ apiVersion: '2006-03-01' });


var LOG_REGEX = /^(.*?)\s(.*?)\s(\[.*?\])\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(\".*?\")\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(.*?)\s(\".*?\")\s(\".*?\")\s(.*?)$/m;

exports.handler = function(event, context) {
    console.log('Received event:', JSON.stringify(event, null, 2));

    var record = event.Records[0];

    // Get the object from the event and show its content type
    var bucket = record.s3.bucket.name;
    var key = record.s3.object.key;

    if (key.substr(0, 5) !== 'logs/') {
        context.succeed('Ignored non-log type: ' + key);
        return;
    }

    var params = {
        Bucket: bucket,
        Key: key
    };
    s3.getObject(params, function(err, data) {
        if (err) {
            console.log("Error getting object " + key + " from bucket " + bucket +
                ". Make sure they exist and your bucket is in the same region as this function.");
            context.fail("Error getting file: " + err);
            return;
        }

        var blobs = [];
        
        var contents = data.Body.toString();
        console.log('Processing ' + contents.length + 'byte log file...');
        contents.split(/\n/).forEach(function(line) {
            if (!line) return;
            var matches = LOG_REGEX.exec(line);
            if (!matches) {
                console.log('Unparsable line: ' + line);
                return;
            }
            // console.log(matches);
            if (matches[7] !== 'REST.GET.OBJECT') return;
            if (matches[10] !== '200') return;
            if (matches[9].indexOf('?x-source=') === -1) return;
            if (matches[9].indexOf('&x-episode=') === -1) return;

            console.log(JSON.stringify(matches));
            blobs.push({
                userAgent: matches[17],
                ip: matches[4],
                source: /x-source=(\w+)/.exec(matches[9])[1],
                episode: /x-episode=([\w-]+)/.exec(matches[9])[1],
                ts: matches[3],
            });
        });
        data = null;

        console.log('Num of logs: ' + blobs.length);
        if (!blobs.length) {
            context.succeed('Nothing to log');
            return;
        }

        var postData = 'payload=' + encodeURIComponent(JSON.stringify(blobs));
        blobs = null;

        console.log('Submitting ' + postData.length + 'byte payload');
        var req = http.request(
            {
                hostname: 'host.podmaster.io',
                port: 80,
                path: '/services/log?access=KEY_HERE',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Content-Length': postData.length,
                },
            },
            function() {
                context.succeed();
            }
        );
        req.on('error', function(e) {
            context.fail(e);
        });
        req.write(postData);
        req.end();

    });
};
