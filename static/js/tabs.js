(function() {

function hide(elem) {
    elem.style.overflow = 'hidden';
    elem.style.height = '0';
}
function show(elem) {
    elem.style.overflow = 'auto';
    elem.style.height = 'auto';
}

function buildTabs(tab) {
    var allTabs = Array.prototype.slice.call(tab.querySelectorAll('li a'));

    function select(a) {
        allTabs.forEach(function(tab) {
            if (tab === a) return;
            tab.className = '';
            hide(document.querySelector(tab.getAttribute('data-tab')));
        });
        a.className = 'selected';
        show(document.querySelector(a.getAttribute('data-tab')));
    }

    tab.addEventListener('click', function(e) {
        e.preventDefault();
        if (e.target.nodeName !== 'A') return;

        select(e.target);
    });

    select(tab.querySelector('li a'));
}

var tabs = document.querySelectorAll('menu.tabs');
Array.prototype.slice.call(tabs).forEach(function(tab) {
    buildTabs(tab);
});

}());
