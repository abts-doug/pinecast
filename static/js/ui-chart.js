(function() {

var chartTypes = {
    line: 'Line',
    pie: 'Doughnut',
};

Chart.defaults.global.responsive = true;
Chart.defaults.global.maintainAspectRatio = false;


var GranularitySelectorOption = React.createClass({
    render: function() {
        return React.createElement(
            'a',
            {
                className: 'chart-granularity-selector-option' + this.selectedText(' is-selected'),
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

var GranularitySelector = React.createClass({
    getInitialState: function() {
        return {
            selected: 'daily',
        };
    },
    render: function() {
        return React.createElement(
            'div',
            {className: 'chart-granularity-selector'},
            this.renderOption('hourly', 'Hour'),
            this.renderOption('daily', 'Day'),
            this.renderOption('weekly', 'Week'),
            this.renderOption('monthly', 'Month')
        );
    },

    renderOption: function(value, text) {
        return React.createElement(
            GranularitySelectorOption,
            {
                value: value,
                name: text,
                selected: this.state.selected,
                setSelected: this.setSelected,
            }
        );
    },

    setSelected: function(value) {
        if (value === this.state.selected) return;
        this.setState({selected: value});
        this.props.onChange(value);
    },
});

var ChartComponent = React.createClass({
    getCanvas: function() {
        var c = document.createElement('canvas');
        c.height = 200;
        c.setAttribute('data-fixed-height', 200);
        c.addEventListener('click', this.startLoadingData);
        return c;
    },

    getInitialState: function() {
        return {
            loadingData: true,
            data: null,

            canvas: this.getCanvas(),
            legend: null,

            xhr: null,

            granularity: 'daily',
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
                this.props.chartType === 'line' ? React.createElement(GranularitySelector, {onChange: this.granularityChanged}) : null
            )
        );
    },

    granularityChanged: function(newGranularity) {
        if (this.state.xhr) {
            this.state.xhr.abort();
        }
        this.cleanSurface();
        this.setState({granularity: newGranularity, xhr: null, data: null, loadingData: true});
    },

    componentDidMount: function() {
        setTimeout(function() {
            this.startLoadingData();
        }.bind(this), Math.random() * 500);
    },

    cleanSurface: function() {
        var surface = this.refs.surface.getDOMNode();
        while (surface.firstChild) surface.removeChild(surface.firstChild);
        var newCanvas = this.getCanvas();
        this.setState({canvas: newCanvas, legend: null})
        surface.appendChild(newCanvas);
        return newCanvas;
    },

    componentDidUpdate: function() {
        if (this.state.loadingData) {
            this.startLoadingData();
            return;
        }
        var canvas = this.cleanSurface();

        var ctx = canvas.getContext('2d');
        var c = new Chart(ctx)[chartTypes[this.props.chartType]](this.state.data);
        if (this.props.hasLegend) {
            this.setState({legend: c.generateLegend()});
        }
    },

    startLoadingData: function() {
        var req = new XMLHttpRequest();
        this.setState({loadingData: true, xhr: req});
        req.onload = function() {
            var parsed = JSON.parse(req.responseText);
            this.setState({
                loadingData: false,
                data: parsed,
                xhr: null,
            });
        }.bind(this);
        req.open(
            'get',
            '/analytics/' + this.props.type +
                '?podcast=' + encodeURIComponent(this.props.podcast) +
                (this.props.episode ? '&episode=' + encodeURIComponent(this.props.episode) : '') +
                (this.props.extra ? '&' + this.props.extra : '') +
                '&interval=' + this.state.granularity,
            true
        );
        req.send();
    },

    shouldComponentUpdate: function(_, nextState) {
        return nextState.loadingData !== this.state.loadingData ||
               nextState.legend !== this.state.legend;
    },

});


var placeholders = document.querySelectorAll('.chart-placeholder');
Array.prototype.slice.call(placeholders).forEach(function(placeholder) {
    React.render(
        React.createElement(ChartComponent, {
            chartType: placeholder.getAttribute('data-chart-type'),
            podcast: placeholder.getAttribute('data-podcast'),
            episode: placeholder.getAttribute('data-episode'),
            type: placeholder.getAttribute('data-type'),
            extra: placeholder.getAttribute('data-extra'),
            title: placeholder.getAttribute('data-title'),
            hasLegend: placeholder.getAttribute('data-has-legend') == 'true',

            origElement: placeholder,
        }),
        placeholder
    );
});

}());
