// Suggestion Functions

function openSuggestionModal() {
  document.getElementById('suggestionModal').classList.add('active');
}

function closeSuggestionModal() {
  document.getElementById('suggestionModal').classList.remove('active');
}

async function submitSuggestion(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  
  try {
    const response = await fetch('/api/metaphor-suggestions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: formData.get('name'),
        email: formData.get('email'),
        suggestion: formData.get('suggestion'),
        reason: formData.get('reason')
      })
    });

    const data = await response.json();
    
    if (response.ok) {
      alert('Thank you for your suggestion! We will review it soon.');
      closeSuggestionModal();
      e.target.reset();
    } else {
      alert(data.error || 'Failed to submit suggestion.');
    }
  } catch (error) {
    alert('Network error. Please try again later.');
  }
}
