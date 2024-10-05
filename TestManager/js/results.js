$(window).on("load", function () {
    getResults();
});

function getResults() {
    $.getJSON("/api/get-results")
    .done(function (response) {
        $("#username").html(`user: ${response.username}`)
        $("#results").html(`${response.score}/30`)
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
        console.log({ jqXHR, textStatus, errorThrown });
    });
}