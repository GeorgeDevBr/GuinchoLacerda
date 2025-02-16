function filtrarGuinchos() {
    const input = document.getElementById('pesquisa');
    const filter = input.value.toLowerCase();
    const rows = document.querySelectorAll('table tbody tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        let match = false;
        cells.forEach(cell => {
            if (cell.textContent.toLowerCase().includes(filter)) {
                match = true;
            }
        });
        row.style.display = match ? '' : 'none';
    });
}
