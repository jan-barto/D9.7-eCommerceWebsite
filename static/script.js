document.addEventListener('DOMContentLoaded', function() {
    const DifferentShippingAddress = document.getElementById('DifferentShippingAddress');
    const ShippingAddress = document.getElementById('ShippingAddress');
    const DeliveryPersonal = document.getElementById('delivery_personal');
    const DeliveryTransport = document.getElementById('delivery_transport');
    const paymentTransfer = document.getElementById('payment_bank_transfer');
    const paymentCod = document.getElementById('payment_cod');
    const paymentHos = document.getElementById('payment_on_spot');

    // Funkce pro zobrazení/skrytí detailů dodání podle stavu checkboxu
    DifferentShippingAddress.addEventListener('change', function() {
        if (this.checked) {
            ShippingAddress.style.display = 'block';
        } else {
            ShippingAddress.style.display = 'none';
        }
        // Při změně způsobu dodání vymažte výběr plateb
        clearPaymentSelection();
    });

    // Funkce pro různé platby v závislosti na způsobu dodání
    function handleDeliveryChange() {
        if (DeliveryPersonal.checked) {
            paymentCod.disabled = true;
            paymentHos.disabled = false;
        } else if (DeliveryTransport.checked) {
            paymentCod.disabled = false;
            paymentHos.disabled = true;
        }
    }

    // Při změně způsobu dodání zavolejte funkci pro různé platby
    DeliveryPersonal.addEventListener('change', function() {
        handleDeliveryChange();
        // Při změně způsobu dodání vymažte výběr plateb
        clearPaymentSelection();
    });

    DeliveryTransport.addEventListener('change', function() {
        handleDeliveryChange();
        // Při změně způsobu dodání vymažte výběr plateb
        clearPaymentSelection();
    });

    // Funkce pro vymazání výběru plateb
    function clearPaymentSelection() {
        paymentTransfer.checked = false;
        paymentCod.checked = false;
        paymentHos.checked = false;
    }

    // Zajištění správného zobrazení detailů dodání při načtení stránky
    if (DifferentShippingAddress.checked) {
        ShippingAddress.style.display = 'block';
    } else {
        ShippingAddress.style.display = 'none';
    }

    // Zajištění správného zobrazení platby při načtení stránky
    handleDeliveryChange();
});
