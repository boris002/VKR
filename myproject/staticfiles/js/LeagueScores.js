function updatePoints(button) {
    var input = button.previousElementSibling;
    var points = input.value;
    var teamId = input.getAttribute('data-team-id');
    var csrfToken = getCookie('csrftoken'); // Функция для получения токена из куки должна быть определена
    
    // Отправляем данные на сервер с использованием AJAX
    $.ajax({
        url: '/update_team_points/',  // Указываем URL, который будет обрабатывать обновление очков
        type: 'POST',
        data: {
            'team_id': teamId,
            'points': points,
            'csrfmiddlewaretoken': csrfToken
        },
        success: function(response) {
            // Обрабатываем успешное обновление
            alert('Очки обновлены');
        }
    });
}
function editTableAndMatches() {
    // Отключаем стандартное отображение и делаем элементы редактируемыми
    var matches = document.querySelectorAll('.match-card');
    var standings = document.querySelectorAll('td');
    
    // Редактирование результатов матчей
    matches.forEach(function(match) {
        var scoreElement = match.querySelector('.score'); // Убедитесь, что у элемента счёта есть класс 'score'
        scoreElement.contentEditable = true; // Делаем элемент счёта редактируемым
        scoreElement.style.backgroundColor = "#eef"; // Опционально меняем фон на редактируемый
    });

    // Редактирование турнирной таблицы
    standings.forEach(function(cell) {
        // Проверка наличия атрибута 'data-team-id', чтобы исключить заголовки таблицы
        if (cell.hasAttribute('data-team-id')) {
            var inputElement = document.createElement('input');
            inputElement.type = 'text';
            inputElement.value = cell.textContent.trim();
            cell.textContent = ''; // Очистка содержимого ячейки
            cell.appendChild(inputElement); // Вставка поля для ввода
            inputElement.focus(); // Фокус на элементе ввода
        }
    });

    // Добавление кнопки "Сохранить изменения"
    var saveButton = document.createElement('button');
    saveButton.textContent = 'Сохранить изменения';
    saveButton.onclick = saveEdits; // Функция saveEdits должна быть определена
    document.querySelector('.container').prepend(saveButton); // Добавление кнопки в начало контейнера
}

function saveEdits() {
    // Здесь код для сохранения изменений, возможно, с отправкой данных через AJAX
    console.log('Изменения сохранены');
    // После сохранения изменений нужно обновить страницу или отменить режим редактирования
}

