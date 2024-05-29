document.getElementById('priceTimeForm').addEventListener('submit', function(event) {
});

document.getElementById('district').addEventListener('change', function(event) {
    const district = event.target.value;
    const stationSelect = document.getElementById('station');
    const stationContainer = document.getElementById('stationContainer');

    stationSelect.innerHTML = '';
    if (stations.length > 0) {
        stationContainer.style.display = 'block';
        stations.forEach(station => {
            const option = document.createElement('option');
            option.value = station;
            option.textContent = station;
            stationSelect.appendChild(option);
        });
    } else {
        stationContainer.style.display = 'none';
    }
});