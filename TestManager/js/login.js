function login() {
    username = $("#username-input").val();
    password = $("#password-input").val();

    $('#login-button').prop( "disabled", true );

    $.post("/login", JSON.stringify({ username: username, password, password }), null, 'json')
        .done(function (response) {
            if (response.status == "SUCCESS") {
                window.location.href = '/test';
            }
            else {
                $('.error-message').replaceWith($('<div>', {class: 'error-message', html: response.message}))
            }
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            console.log({ jqXHR, textStatus, errorThrown });
        })
        .always(function() {
            $('#login-button').prop( "disabled", false );
        })
}
