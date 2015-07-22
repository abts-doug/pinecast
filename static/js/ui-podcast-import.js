(function() {

function request(method, url, body, onload, onerror) {
    var xhr = new XMLHttpRequest();
    xhr.onload = function() {
        if (xhr.status !== 200) onerror(xhr.responseText);
        else onload(xhr.responseText);
    };
    xhr.onerror = onerror;
    xhr.open(method, url, true);

    if (typeof body === 'string') {
        body += '&csrfmiddlewaretoken=' + encodeURIComponent(this.props.csrf);
    } else if (body && typeof body === 'object') {
        body.append('csrfmiddlewaretoken', this.props.csrf);
    }

    xhr.send(body);
    return xhr;
}

var SlugField = React.createClass({
    propTypes: {
        validityCB: React.PropTypes.func.isRequired,
        valueCB: React.PropTypes.func.isRequired,
    },
    getInitialState: function() {
        return {
            checkTimeout: null,
            checkXHR: null,

            isValid: null,
        };
    },

    render: function() {
        return React.createElement(
            'label',
            {},
            React.createElement('span', {}, 'Slug'),
            React.createElement(
                'input',
                {
                    className: 'slug-field width-full',
                    maxlength: 64,
                    pattern: '[\\w-]+',
                    placeholder: 'my-great-podcast',
                    ref: 'inp',
                    required: true,
                    type: 'text',
                    readOnly: this.props.readonly,

                    onInput: this.checkValidity,
                }
            ),
            this.state.isValid === null ? null : React.createElement(
                'div',
                {className: 'url-availability ' + (this.state.isValid ? 'is-available' : 'is-unavailable')},
                this.state.isValid ? 'The slug is available!' : 'The slug is unavailable.'
            )
        );
    },

    checkValidity: function() {
        this.setState({isValid: null});

        if (this.state.checkXHR) {
            this.state.checkXHR.abort();
            this.setState({checkXHR: null});
        }
        if (this.state.checkTimeout) {
            clearTimeout(this.state.checkTimeout);
            this.setState({checkTimeout: null});
        }

        var node = this.refs.inp.getDOMNode();
        if (!node.validity.valid || !node.value) {
            this.props.validityCB(false);
            return;
        } else {
            this.props.validityCB(true);
        }

        this.props.valueCB(node.value);
        this.setState({checkTimeout: setTimeout(this.doCheck, 500)});
    },
    doCheck: function() {
        var node = this.refs.inp.getDOMNode();
        var req = this.req(
            'get',
            '/dashboard/services/slug_available?slug=' + encodeURIComponent(node.value),
            null,
            function(responseText) {
                var parsed = JSON.parse(responseText);
                this.setState({isValid: parsed.valid});
            }.bind(this)
        );
    },

    req: request,
});

var PodcastImporter = React.createClass({

    getInitialState: function() {
        return {
            step: 1,
            step1error: null,
            step2loaded: false,
            step2error: null,
            slugValue: null,
            slugValid: false,

            podcastData: null,
        };
    },

    render: function() {
        return React.createElement(
            'div',
            {},
            !this.state.step1error ? null : React.createElement(
                'div',
                {className: 'error'},
                this.state.step1error
            ),
            this.getStep1(),
            this.getStep2(),
            this.getStep3()
        );
    },

    getStep1: function() {
        return React.createElement(
            'div',
            {className: 'card card-block'},
            React.createElement('strong', {}, 'Step One'),
            this.state.step !== 1 ? null : React.createElement('p', {}, 'Enter the feed URL of your existing podcast'),
            React.createElement(
                'label',
                {},
                React.createElement('span', {}, 'Feed URL'),
                React.createElement(
                    'input',
                    {
                        type: 'url',
                        ref: 's1url',
                        placeholder: 'http://wtfpod.libsyn.com/rss',
                        readOnly: this.state.step !== 1,
                    }
                )
            ),
            this.state.step !== 1 ? null : React.createElement(
                'button',
                {
                    onClick: this.downloadFeed,
                },
                'Continue'
            )
        );
    },
    getStep2: function() {
        if (this.state.step < 2) {
            return null;
        }

        if (!this.state.step2loaded) {
            return React.createElement(
                'div',
                {className: 'card card-block'},
                React.createElement('strong', {}, 'Step Two'),
                React.createElement('p', {}, 'Loading feed information...')
            );
        }

        return React.createElement(
            'div',
            {className: 'card card-block'},
            React.createElement('strong', {}, 'Step Two'),
            this.state.step !== 2 ? null : React.createElement('p', {}, 'Review the feed information below'),
            this.renderPodcastData(),
            React.createElement('hr'),
            !this.state.step2error ? null : React.createElement('div', {className: 'error'}, this.state.step2error),
            this.state.step !== 2 ? null : React.createElement('p', {}, 'Please choose a slug for the podcast.'),
            React.createElement(
                SlugField,
                {
                    readonly: this.state.step !== 2,
                    validityCB: function(valid) {
                        this.setState({slugValid: valid});
                    }.bind(this),
                    valueCB: function(value) {
                        this.setState({slugValue: value});
                    }.bind(this),
                }
            ),
            this.state.step !== 2 ? null : React.createElement(
                'menu',
                {className: 'toolbar'},
                React.createElement(
                    'li',
                    {},
                    React.createElement(
                        'button',
                        {
                            onClick: this.beginImport,
                        },
                        'Continue'
                    )
                ),
                React.createElement(
                    'li',
                    {},
                    React.createElement(
                        'button',
                        {
                            className: 'btn-neutral',
                            onClick: this.backToStep1,
                        },
                        'Try Again'
                    )
                )
            )
        );
    },
    getStep3: function() {
        if (this.state.step < 3) {
            return null;
        }

        return React.createElement(
            'div',
            {className: 'card card-block'},
            React.createElement('strong', {}, 'Step Three'),
            this.getStep3ProgressText(),
            React.createElement(
                'div',
                {className: 'progress'},
                React.createElement('i', {width: this.getStep3Progress()})
            )
        );
    },

    backToStep1: function() {
        this.setState({
            step: 1,
            step1error: null,
            step2loaded: false,
        });
    },

    downloadFeed: function() {
        var val = this.refs.s1url.getDOMNode().value;
        if (!val) {
            this.setState({step1error: 'You must enter a feed URL'});
            return;
        }
        this.setState({step: 2, step1error: null});

        this.req(
            'get',
            '/dashboard/import/feed?url=' + encodeURIComponent(val),
            null,
            function(responseText) {
                var parsed = JSON.parse(responseText);
                if (parsed.error) {
                    switch(parsed.error) {
                        case 'protocol':
                            this.setState({step: 1, step1error: 'The URL you provided must start with http:// or https://'});
                            return;
                        case 'connection':
                            this.setState({step: 1, step1error: 'Could not download a feed at that URL'});
                            return;
                        case 'invalid encoding':
                            this.setState({step: 1, step1error: 'We were able to download the feed, but it had a bad encoding.'});
                            return;
                        case 'invalid xml':
                            this.setState({step: 1, step1error: 'We were able to download the feed, but could not parse it. Try validating your feed first.'});
                            return;
                        case 'invalid format':
                            this.setState({step: 1, step1error: parsed.details});
                            return;
                    }
                    return;
                }
                this.setState({
                    step2loaded: true,
                    podcastData: parsed,
                });
            }.bind(this),
            function() {
                this.setState({
                    step: 1,
                    step1error: 'Could not connect to PodMaster',
                })
            }.bind(this)
        );
    },

    renderPodcastData: function() {
        var data = this.state.podcastData;

        function nullStyle(obj, val) {
            if (val) return obj;
            obj.style = {'font-style': 'italic'};
            return obj
        }

        return React.createElement(
            'div',
            {
                className: 'podcast-import-data',
                style: {
                    'min-height': '200px',
                    'padding-left': '220px',
                    position: 'relative',
                },
            },
            React.createElement(
                'img',
                {
                    className: 'podcast-import-coverimage',
                    src: data.cover_image,
                    style: {
                        height: '200px',
                        left: 0,
                        position: 'absolute',
                        top: 0,
                        width: '200px',
                    },
                }
            ),
            React.createElement('hgroup', {},
                React.createElement('h1', {className: 'podcast-import-title'}, data.name),
                React.createElement('h2', nullStyle(data.subtitle, {className: 'podcast-import-subtitle'}), data.subtitle || 'No Subtitle')
            ),
            React.createElement(
                'div',
                {
                    className: 'podcast-import-description',
                    dangerouslySetInnerHTML: {__html: data.description},
                    style: {margin: '20px 10px'},
                }
            ),
            React.createElement('h3', {}, 'Categories'),
            React.createElement(
                'ul',
                {
                    style: {
                        'line-height': '20px',
                        margin: '10px 0',
                    },
                },
                data.categories.map(function(c) {
                    return React.createElement('li', {}, c);
                })
            ),
            React.createElement('h3', {}, 'Details'),
            React.createElement(
                'dl',
                {
                    style: {padding: '15px'},
                },
                React.createElement('dt', {}, 'Homepage'),
                React.createElement('dd', {}, data.homepage),
                
                React.createElement('dt', {}, 'Language'),
                React.createElement('dd', {}, data.language),
                
                React.createElement('dt', {}, 'Copyright'),
                React.createElement('dd', {}, data.copyright),
                
                React.createElement('dt', {}, 'Author Name'),
                React.createElement('dd', {}, data.author_name),
                
                React.createElement('dt', {}, 'Explicit?'),
                React.createElement('dd', {}, data.is_explicit ? 'Yes' : 'No')
                
            ),

            React.createElement('h3', {}, 'Items'),
            React.createElement('p', {style: {padding: '0 10px'}}, 'There are ' + data.items.length + ' episodes in this podcast.'),
            
            React.createElement(
                'table',
                {
                    style: {
                        border: '1px solid #eee',
                        'box-shadow': 'none',
                    },
                },
                React.createElement('thead', {},
                    React.createElement('tr', {},
                        React.createElement('th', {}, 'Episode Name'),
                        React.createElement('th', {}, 'Subtitle')
                    )
                ),
                React.createElement('tbody', {},
                    data.items.slice(0, 10).map(function(i) {
                        //
                        return React.createElement('tr', {},
                            React.createElement('td', {}, i.title),
                            React.createElement('td', nullStyle({}, i.subtitle), i.subtitle || 'No Subtitle')
                        )
                    })
                )
            ),
            data.items.length > 10 ? React.createElement(
                'p',
                {style: {'font-style': 'italic', 'padding-left': '10px'}},
                (data.items.length - 10) + ' item(s) not shown'
            ) : null,
            !this.state.podcastData.__ignored_items ? null : React.createElement(
                'div',
                {className: 'warning'},
                'Warning! We found ' + this.state.podcastData.__ignored_items + ' items in your ' +
                'feed that did not have an <enclosure /> tag. There was no audio attached to these ' +
                'items, so we cannot import them.'
            )
        );
    },

    beginImport: function() {
        if (!this.state.slugValue || !this.state.slugValid) {
            this.setState({step2error: 'You must find an available slug before proceeding'});
            return;
        }
        this.setState({step: 3, step3process: 'submitting'});

        var body = new FormData();
        for (var key in this.state.podcastData) {
            if (!this.state.podcastData.hasOwnProperty(key)) continue;
            if (key === 'items') continue;
            if (key.substr(0, 2) === '__') continue;
            body.append(key, this.state.podcastData[key]);
        }
        body.append('slug', this.state.slugValue);
        body.append('items', JSON.stringify(this.state.podcastData.items));
        this.req('post', '/dashboard/services/start_import', body, this.importStarted, this.importError);
    },

    importStarted: function() {},
    importError: function() {},

    getStep3Progress: function() {},
    getStep3ProgressText: function() {},

    req: request,

});

var placeholders = document.querySelectorAll('.importer-placeholder');
Array.prototype.slice.call(placeholders).forEach(function(placeholder) {
    React.render(
        React.createElement(PodcastImporter, {
            origElement: placeholder,
            csrf: placeholder.getAttribute('data-csrf'),
        }),
        placeholder
    );
});

}());
