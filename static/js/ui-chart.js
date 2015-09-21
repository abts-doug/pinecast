(function() {

var chartTypes = {
    line: 'Line',
    pie: 'Doughnut',
};

Chart.defaults.global.responsive = true;
Chart.defaults.global.maintainAspectRatio = false;


var ChartOption = React.createClass({
    render: function() {
        return React.createElement(
            'a',
            {
                className: 'chart-option' + this.selectedText(' is-selected'),
                onClick: this.click,
            },
            this.props.name
        );
    },

    selectedText: function(text) {
        if (this.props.value !== this.props.selected) return '';
        return text;
    },

    click: function() {
        this.props.setSelected(this.props.value);
    }
});

var ChartOptionSelector = React.createClass({
    render: function() {
        return React.createElement(
            'div',
            {className: 'chart-option-selector'},
            this.renderOptions()
        );
    },

    renderOptions: function() {
        return Object.keys(this.props.options).map(function(option) {
            return this.renderOption(option, this.props.options[option]);
        }.bind(this));
    },

    renderOption: function(value, text) {
        return React.createElement(
            ChartOption,
            {
                value: value,
                name: text,
                selected: this.props.defaultSelection,
                setSelected: this.setSelected,
            }
        );
    },

    setSelected: function(value) {
        if (value === this.props.defaultSelection) return;
        this.props.onChange(value);
    },
});

var ChartComponent = React.createClass({
    getCanvas: function() {
        var c = document.createElement('canvas'); 
        c.height = 200;
        c.setAttribute('data-fixed-height', 200);
        return c;
    },

    getGranularities: function(newTimeframe) {
        var output = {};
        switch (newTimeframe || this.state.timeframe) {
            case 'day':
                return {hourly: gettext('Hourly')};
            case 'month':
            case 'sixmonth':
                output.daily = gettext('Day');
            case 'year':
                output.weekly = gettext('Week');
            case 'all':
                output.monthly = gettext('Month');
        }

        return output;
    },

    getTimeframes: function() {
        var tfs = {
            day: gettext('Today'),
            month: gettext('30d'),
            sixmonth: gettext('6m'),
            year: gettext('1y'),
            all: gettext('All'),
        };

        var atsRaw = this.props.availableTimeframes;
        if (!atsRaw) return tfs;

        var ats = atsRaw.split(',');
        if (!ats.length) return tfs;

        Object.keys(tfs).forEach(function(tf) {
            if (ats.indexOf(tf) === -1) {
                delete tfs[tf];
            }
        });

        return tfs;
    },

    getInitialState: function() {
        return {
            data: null,
            legend: null,

            xhr: null,

            granularity: 'daily',
            timeframe: 'month',
        };
    },

    render: function() {
        return React.createElement(
            'div',
            {
                style: {
                    'box-sizing': 'content-box',
                },
            },
            (this.props.title ? React.createElement('strong', {className: 'chart-title', title: this.props.title}, this.props.title) : null),
            this.state.legend ? React.createElement('div', {
                dangerouslySetInnerHTML: {__html: this.state.legend}
            }) : null,
            React.createElement('div', {ref: 'surface'}),
            React.createElement(
                'div',
                {className: 'chart-toolbar'},
                !this.props.hideGranularity && this.props.chartType === 'line' ?
                    React.createElement(ChartOptionSelector, {
                        onChange: this.granularityChanged,
                        options: this.getGranularities(),
                        defaultSelection: this.state.granularity,
                    }) :
                    null,
                !this.props.hideTimeframe ?
                    React.createElement(ChartOptionSelector, {
                        onChange: this.timeframeChanged,
                        options: this.getTimeframes(),
                        defaultSelection: this.state.timeframe,
                    }) :
                    null
            )
        );
    },

    granularityChanged: function(newGranularity) {
        if (this.state.xhr) {
            this.state.xhr.abort();
        }
        this.cleanSurface();
        this.setState({granularity: newGranularity, xhr: null, data: null});
        setTimeout(this.startLoadingData, 0);
    },

    timeframeChanged: function(newTimeframe) {
        if (this.state.xhr) {
            this.state.xhr.abort();
        }
        this.cleanSurface();
        this.setState({timeframe: newTimeframe, xhr: null, data: null});

        var granularities = this.getGranularities(newTimeframe);
        if (!(this.state.granularity in granularities)) {
            this.setState({granularity: Object.keys(granularities)[0]});
        }
        setTimeout(this.startLoadingData, 0);
    },

    componentDidMount: function() {
        setTimeout(this.startLoadingData, Math.random() * 500);
    },

    cleanSurface: function() {
        var surface = this.refs.surface.getDOMNode();
        while (surface.firstChild) surface.removeChild(surface.firstChild);
        var newCanvas = this.getCanvas();
        this.setState({canvas: newCanvas, legend: null})
        surface.appendChild(newCanvas);
        return newCanvas;
    },

    startLoadingData: function() {
        var req = new XMLHttpRequest();
        this.setState({xhr: req});
        req.onload = function() {
            var parsed = JSON.parse(req.responseText);
            this.setState({data: parsed, xhr: null});

            var canvas = this.cleanSurface();

            var ctx = canvas.getContext('2d');
            var c = new Chart(ctx)[chartTypes[this.props.chartType]](this.state.data);
            if (this.props.hasLegend) {
                this.setState({legend: c.generateLegend()});
            }
        }.bind(this);
        req.open(
            'get',
            '/analytics/' + this.props.type +
                '?podcast=' + encodeURIComponent(this.props.podcast) +
                (this.props.episode ? '&episode=' + encodeURIComponent(this.props.episode) : '') +
                (this.props.extra ? '&' + this.props.extra : '') +
                '&interval=' + this.state.granularity +
                '&timeframe=' + this.state.timeframe,
            true
        );
        req.send();
    },

});


var placeholders = document.querySelectorAll('.chart-placeholder');
Array.prototype.slice.call(placeholders).forEach(function(placeholder) {
    React.render(
        React.createElement(ChartComponent, {
            chartType: placeholder.getAttribute('data-chart-type'),
            hideGranularity: !!placeholder.getAttribute('data-hide-granularity'),
            hideTimeframe: !!placeholder.getAttribute('data-hide-timeframe'),
            podcast: placeholder.getAttribute('data-podcast'),
            episode: placeholder.getAttribute('data-episode'),
            type: placeholder.getAttribute('data-type'),
            extra: placeholder.getAttribute('data-extra'),
            title: placeholder.getAttribute('data-title'),
            hasLegend: placeholder.getAttribute('data-has-legend') == 'true',
            availableTimeframes: placeholder.getAttribute('data-timeframes') || '',

            origElement: placeholder,
        }),
        placeholder
    );
});

}());
