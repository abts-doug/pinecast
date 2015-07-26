console.log('Loading function');


var http = require('http');
var https = require('https');
var url = require('url');

exports.handler = function(event, context) {
    console.log('Received event:', JSON.stringify(event, null, 2));

    var token = event.token;
    var feedURL = event.url;

    http.get('https://host.podmaster.io/dashboard/services/check_request_token?token=' + encodeURIComponent(token), function(res) {
        var content = '';
        res.on('data', function(d) {
            content += d.toString();
        });
        res.on('close', function() {
            var data = JSON.parse(content);
            if (!data.success) {
                console.fail('Invalid request token: ' + token);
            }

            processFeed(feedURL);
        });
    }).on('error', function(e) {
        console.error(e);
        console.fail('Could not validate request token from host server');
    });

    function processFeed(feedURL) {
        var parsed = url.parse(feedURL);
        var handler = parsed.protocol === 'https:' ? https : http;

        parsed.method = 'GET';
        parsed.headers = {'agent': 'PodMaster/Importer 1.0'};
        var req = handler.request(parsed, function(res) {
            if (res.headers.location) {
                processFeed(res.headers.location);
                return;
            }

            var content = '';
            res.on('data', function(d) {
                content += d.toString();
            });
            res.on('close', function() {
                context.succeed(content);
            });
        });
        req.on('error', function(e) {
            context.fail(e);
        });
        req.end();
    }

};
