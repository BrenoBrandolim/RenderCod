document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;

    // Verifica o tema salvo no localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        body.classList.remove('light-mode', 'dark-mode'); // Remove ambos antes de adicionar
        body.classList.add(savedTheme);
    } else {
        // Define um tema padrão se não houver um salvo (ex: light-mode)
        body.classList.add('light-mode');
    }

    themeToggle.addEventListener('click', () => {
        if (body.classList.contains('light-mode')) {
            body.classList.remove('light-mode');
            body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark-mode');
        } else {
            body.classList.remove('dark-mode');
            body.classList.add('light-mode');
            localStorage.setItem('theme', 'light-mode');
        }
    });

    // Adiciona evento para o campo de preço do prato dinâmico
    const pratoPrecoInput = document.getElementById('prato_preco');
    if (pratoPrecoInput) {
        pratoPrecoInput.addEventListener('input', formatPriceInput);
    }

    // Adiciona evento para o campo de preço da sobremesa dinâmica
    const sobremesaPrecoInput = document.getElementById('sobremesa_preco');
    if (sobremesaPrecoInput) {
        sobremesaPrecoInput.addEventListener('input', formatPriceInput);
    }

    function formatPriceInput(event) {
        let value = event.target.value;
        // Permite apenas números e uma vírgula/ponto para decimal
        value = value.replace(/[^0-9,.]/g, '');
        // Substitui vírgula por ponto (para parseFloat funcionar)
        value = value.replace(',', '.');
        // Garante apenas um ponto decimal
        const parts = value.split('.');
        if (parts.length > 2) {
            value = parts[0] + '.' + parts.slice(1).join('');
        }
        // Garante no máximo 2 casas decimais após o ponto
        if (parts[1] && parts[1].length > 2) {
            value = parts[0] + '.' + parts[1].substring(0, 2);
        }
        event.target.value = value;
    }
});