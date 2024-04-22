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
