(function() {

var PodcastImporter = React.createClass({

    getInitialState: function() {
        return {
            step: 1,
            step1error: null,
            step2loaded: false,

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
            React.createElement('p', {}, 'Enter the feed URL of your existing podcast'),
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
            React.createElement('p', {}, 'Review the feed information below'),
            this.renderPodcastData(),
            React.createElement(
                'menu',
                {className: 'toolbar'},
                React.createElement(
                    'li',
                    {},
                    React.createElement(
                        'button',
                        {
                            onClick: this.downloadFeed,
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
    getStep3: function() {},

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
        var xhr = new XMLHttpRequest();

        xhr.onload = function() {
            if (xhr.status !== 200) {
                return xhr.onerror();
            }
            var parsed = JSON.parse(xhr.responseText);
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
        }.bind(this);
        xhr.onerror = function() {
            this.setState({
                step: 1,
                step1error: 'Could not connect to PodMaster',
            })
        }.bind(this);

        xhr.open('get', '/dashboard/import/feed?url=' + encodeURIComponent(val), true);
        xhr.send();
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
                }
            ),
            React.createElement('h3', {}, 'Categories'),
            React.createElement('ul', {},
                data.categories.map(function(c) {
                    return React.createElement('li', {}, c);
                })
            ),
            React.createElement('h3', {}, 'Details'),
            React.createElement('dl', {},
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
            React.createElement('p', {}, 'There are ' + data.items.length + ' episodes in this podcast.')

        );
    },

});

var placeholders = document.querySelectorAll('.importer-placeholder');
Array.prototype.slice.call(placeholders).forEach(function(placeholder) {
    React.render(
        React.createElement(PodcastImporter, {
            origElement: placeholder,
        }),
        placeholder
    );
});

}());
