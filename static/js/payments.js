(function() {

Stripe.setPublishableKey(document.querySelector('[data-publishable-key]').getAttribute('data-publishable-key'));

var paymentInfoForm = document.querySelector('.payment-info-form');
if (paymentInfoForm) {
    paymentInfoForm.addEventListener('submit', function(e) {
        e.preventDefault();

        var elems = e.target.elements;
        Stripe.card.createToken({
            name: elems.name.value,
            address_zip: elems.address_zip.value,
            number: elems.number.value,
            cvc: elems.cvc.value,
            exp_month: elems.exp_month.value,
            exp_year: elems.exp_year.value,
        }, oneTimeUseCB);

        function oneTimeUseCB(status, resp) {
            if (status !== 200) {
                console.error(status.toString() + ' response from Stripe!');
            }
            if (resp.error) {
                var errorBox = paymentInfoForm.querySelector('.error');
                errorBox.textContent = errorBox.innerText = resp.error.message;
                return;
            }

            var token = resp.id;
            console.log(token);
        }

    });
}

}());
