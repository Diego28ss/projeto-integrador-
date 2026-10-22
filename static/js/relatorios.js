function abrirModalCancelar(id) {
    document.getElementById('cancel_venda_id').value = id;
    document.getElementById('cancel_venda_display').innerText = id;
    var myModal = new bootstrap.Modal(document.getElementById('modalCancelar'));
    myModal.show();
}
