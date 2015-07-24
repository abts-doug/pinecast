console.log('Loading function');


var http = require('http');
var https = require('https');
var querystring = require('querystring');
var url = require('url');

var aws = require('aws-sdk');
var s3 = new aws.S3({ apiVersion: '2006-03-01' });

exports.handler = function(event, context) {
    // console.log('Received event:', JSON.stringify(event, null, 2));

    var record = event.Records[0].Sns.Message;
    record = JSON.parse(record);
    var parsed = url.parse(record.url);
    var handler = parsed.protocol === 'https:' ? https : http;

    parsed.method = 'GET';
    parsed.headers = {'agent': 'PodMaster/Importer 1.0'};
    var req = handler.request(parsed, function(res) {
        console.log('Got response back from server');
        if (res.statusCode < 200 || res.statusCode > 299) {
            postFailure('Invalid status code: ' + res.statusCode);
            return;
        }

        console.log('Response was a 2XX response');
        var contentLength = res.headers['content-length'];
        if (!contentLength) {
            console.log('No Content-Length was found');
            postFailure('No Content-Length was provided for the object');
            return;
        }
        console.log('Content-Length: ' + contentLength);

        // Hack to work around https://github.com/aws/aws-sdk-js/issues/94
        res.length = contentLength | 0;

        console.log('Bucket: ' + record.bucket);
        console.log('Key: ' + record.key);
        var params = {
            Bucket: record.bucket,
            Key: record.key,
            Body: res,
            ContentType: res.headers['content-type'],
            ACL: 'public-read',
        };
        s3.putObject(params, function(err) {
            if (err) {
                postFailure('Error posting to S3: ' + err);
                return;
            }
            console.log('Object posted successfully');
            postSuccess('http://' + params.Bucket + '.s2.amazonaws.com/' + params.Key);
        });
    });
    req.on('error', function(e) {
        postFailure(e)
    });
    req.end();

    function postFailure(e) {
        console.error('Terminating because of error');
        console.error(e);
        e = e.toString();
        if (!record.cb_url) {
            context.fail(e);
            return;
        }
        var postData = getPOSTData({failed: true, error: e});
        var parsed = getCBUrl(postData);
        var req = http.request(parsed, function() {
            context.fail(e);
        });
        req.on('error', function(e) {
            console.error('Something went really wrong');
            console.error(e);
            context.fail(e);
        });
        req.write(postData);
        req.end();
    }

    function postSuccess(newUrl) {
        if (!record.cb_url) {
            console.log('No callback url provided, quitting');
            context.succeed(newUrl);
            return;
        }
        var postData = getPOSTData({url: newUrl});
        var parsed = getCBUrl(postData);
        var req = http.request(parsed, function() {
            context.succeed(newUrl);
        });
        req.on('error', function(e) {
            postFailure(e);
        });
        req.write(postData);
        req.end();
    }

    function getPOSTData(data) {
        data.token = record.token;
        data.id = record.id;
        return querystring.stringify(data);
    }

    function getCBUrl(postData) {
        var parsed = url.parse(record.cb_url);
        parsed.method = 'POST';
        parsed.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': postData.length,
        };
        return parsed;
    }
};
