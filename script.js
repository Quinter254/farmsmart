function payWithMpesa(amount) {
  fetch('/pay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message);
  })
  .catch(err => alert("Payment failed"));
}

