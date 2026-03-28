document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const required = form.querySelectorAll('[required]');
            let valid = true;

            required.forEach(field => {
                let fieldValid = true;

                if (field.type === 'checkbox' || field.type === 'radio') {
                    if (!field.checked) {
                        fieldValid = false;
                    }
                } else {
                    if (!field.value || !field.value.trim()) {
                        fieldValid = false;
                    }
                }

                if (!fieldValid) {
                    valid = false;
                    field.style.borderColor = 'red';
                } else {
                    field.style.borderColor = '#ddd';
                }
            });

            if (!valid) {
                e.preventDefault();
                alert('Preencha todos os campos obrigatórios!');
            }
        });
    });
});