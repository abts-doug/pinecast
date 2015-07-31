(function() {

var chartTypes = {
    line: 'Line',
    pie: 'Doughnut',
};

Chart.defaults.global.responsive = true;
Chart.defaults.global.maintainAspectRatio = false;


var ChartComponent = React.createClass({

    getInitialState: function() {
        var c = document.createElement('canvas');
        c.height = 200;
        c.setAttribute('data-fixed-height', 200);
        c.addEventListener('click', this.startLoadingData);

        return {
            loadingData: true,
            data: null,

            canvas: c,
            legend: null,
            chart: null,
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
            React.createElement('div', {ref: 'surface'})
        );
    },

    componentDidMount: function() {
        setTimeout(function() {
            this.startLoadingData();
        }.bind(this), Math.random() * 1000);
    },

    componentDidUpdate: function() {
        if (this.state.loadingData) {
            this.startLoadingData();
            return;
        }
        this.refs.surface.getDOMNode().appendChild(this.state.canvas);
        var ctx = this.state.canvas.getContext('2d');
        var c = new Chart(ctx)[chartTypes[this.props.chartType]](this.state.data);
        if (this.props.hasLegend) {
            this.setState({
                legend: c.generateLegend(),
            });
        }
    },

    startLoadingData: function() {
        this.setState({loadingData: true});
        var req = new XMLHttpRequest();
        req.onload = function() {
            var parsed = JSON.parse(req.responseText);
            this.setState({
                loadingData: false,
                data: parsed,
            });
        }.bind(this);
        req.open(
            'get',
            '/analytics/' + this.props.type +
                '?podcast=' + encodeURIComponent(this.props.podcast) +
                (this.props.episode ? '&episode=' + encodeURIComponent(this.props.episode) : '') +
                '&timezone=' + encodeURIComponent(-new Date().getTimezoneOffset() / 60) +
                (this.props.extra ? '&' + this.props.extra : ''),
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
