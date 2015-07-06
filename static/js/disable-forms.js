(function() {

Array.prototype.slice.call(document.querySelectorAll('form')).forEach(function(f) {
    f.addEventListener('submit', function() {
        f.querySelector('button[type="submit"]').disabled = true;
    });
});

}());
