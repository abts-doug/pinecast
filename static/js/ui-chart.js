(function() {

var chartTypes = {
    line: 'Line',
    pie: 'Doughnut',
};

var ChartComponent = React.createClass({

    getInitialState: function() {
        return {
            loadingData: true,
            data: null,

            chart: null,
        };
    },

    render: function() {
        return React.createElement(
            'div',
            {},
            (this.props.title ? React.createElement('span', {className: 'chart-title'}, this.props.title) : null),
            React.createElement(
                'canvas',
                {
                    ref: 'surface',
                    width: this.props.origElement.clientWidth - 30,
                    height: 200,
                }
            )
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
        var ctx = this.refs.surface.getDOMNode().getContext('2d');
        var c = new Chart(ctx)[chartTypes[this.props.chartType]](this.state.data);
        this.setState({chart: c});
    },

    startLoadingData: function() {
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
                '&timezone=' + encodeURIComponent(-new Date().getTimezoneOffset() / 60),
            true
        );
        req.send();
    },

    shouldComponentUpdate: function(_, nextState) {
        return nextState.loadingData !== this.state.loadingData;
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
            title: placeholder.getAttribute('data-title'),

            origElement: placeholder,
        }),
        placeholder
    );
});

}());
