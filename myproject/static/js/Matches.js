function showContent(contentId) {
    // Скрыть все блоки контента
    var contentBlocks = document.querySelectorAll('.content-block');
    for (var i = 0; i < contentBlocks.length; i++) {
        contentBlocks[i].style.display = 'none';
    }

    // Показать выбранный блок контента
    document.getElementById(contentId).style.display = 'block';
}

// Показать первый блок контента по умолчанию
showContent('standings');
