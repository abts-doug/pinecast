(function() {

Array.prototype.slice.call(document.querySelectorAll('.publish-now')).forEach(function(f) {
    f.addEventListener('click', function(e) {
        e.preventDefault();
        var now = new Date();
        var timezoneOffset = now.getTimezoneOffset() * 60 * 1000;
        var localDate = new Date(now.getTime() - timezoneOffset);
        e.target.parentNode.querySelector('input').value = localDate.toISOString().replace(/:\d+\.\d+z/ig, '');
    });
});

}());
