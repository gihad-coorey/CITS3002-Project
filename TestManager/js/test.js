currentQuestion = 1;

$(window).on("load", function () {
    // test whether the user is logged in correctly & questions are available
    // Get question 1 when the user loads the page
    getQuestion(1);
    $(".question-link").on("click", function (e) {
        getQuestion(e.target.dataset.question);
    });
});
function getQuestion(num) {
    currentQuestion = parseInt(num);
    $.getJSON("/api/get-question?question=" + num)
        .done(function (response) {
            if (response.type == "MultiChoice") $(".question-content").replaceWith(multiChoiceQuestion(num, response.content, response.options));
            else $(".question-content").replaceWith(programmingQuestion(num, response.content, response.language));

            manageAttemptCount(response.state, response.attempt);

            manageAnswerDisplay(response.state != "active", response.state == 'correct', response.student_output, response.expected_output, response.type);

            $("#current-score").html(response.score);

            if (response.finished) {
                window.location.href = "/results";
            }

            if (response.state != "active") {
                $(".submit-question").prop("disabled", true);
            }
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            console.log({ jqXHR, textStatus, errorThrown });
            $(".question-content").replaceWith(errorQuestion(jqXHR.responseText));
        });
}

function submitQuestion() {
    var formContainer = document.getElementById("submission-container");
    var form = formContainer.querySelector("form");

    if (!form) {
        console.log("No form found.");
        return;
    }
    jsonPayload = JSON.stringify(parseForm(form));
    // problem below
    $.post("/api/submit-question", jsonPayload, null, "json")
        .done(function (response) {
            if (response.status != "FAIL") {
                manageAttemptCount(response.state, response.attempt);
                manageAnswerDisplay(response.state != "active", response.state == 'correct', response.student_output, response.expected_output, response.type);
                document.getElementById("current-score").innerHTML = response.score;
            }
            if (response.finished) {
                window.location.href = "/results";
            }
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            console.log({ jqXHR, textStatus, errorThrown });
        });
}

function manageAttemptCount(state, attempt) {
    attempts = $(".question-attempt").first();
    attempt--;
    if (state == "wrong") {
        attempts.children().each(function (index) {
            this.className = "attempt-box wrong";
        });
    } else {
        attempts.children().each(function (index) {
            if (attempt > index) this.className = "attempt-box wrong";
            else if (attempt == index) this.className = `attempt-box ${state}`;
            else this.className = "attempt-box";
        });
    }
}

function manageAnswerDisplay(isFinal, isCorrect, attempt, answer, type) {
    if (isFinal) {
        $("#submit-button").css("display", "none");
        $(".question-answer").removeAttr("style");

        if (isCorrect) {
            $(".student-answer").toggleClass('correct', true)
        }
        else {
            $(".student-answer").toggleClass('correct', false)
        }
        if (type == "MultiChoice") {
            form = $(".option").first();
            labels = form.children("label");
            buttons = form.children("input");

            buttons.each(function (i) {
                this.disabled = true;
            });

            $(".student-answer-content").html(labels.eq(parseInt(attempt) - 1).html());
            $(".expected-answer-content").html(labels.eq(parseInt(answer) - 1).html());
        } else {
            $(".student-answer-content").html(attempt);
            $(".expected-answer-content").html(answer);
        }
    } else {
        $("#submit-button").removeAttr("style");
        $(".question-answer").css("display", "none");
        $(".student-answer-content").html("");
        $(".expected-answer-content").html("");

        if (type == "MultiChoice") {
            form = $(".option").first();
            buttons = form.children("input");
            buttons.each(function (i) {
                this.disabled = false;
            });
        }
    }
}

function parseForm(form) {
    var payload = {};

    // Parse the form fields based on their type
    for (var i = 0; i < form.elements.length; i++) {
        var input = form.elements[i];
        var value = "uninitialised value";
        if (input.type === "radio") {
            if (input.checked) {
                value = (i + 1).toString(); // index of the option selected
                break;
            }
        } else if (input.type === "textarea") {
            {
                value = input.value;
                break;
            }
        }
    }

    // Add additional key-value pairs to the payload
    payload["question"] = currentQuestion;
    payload["attempt"] = value;

    return payload;
}

function multiChoiceQuestion(number, question, options) {
    return $(
        $.parseHTML(`
            <div class="question-content" id="submission-container">
                <div class="question-number">Q${number}</div>
                <div class="question-content">${question}</div>
                <form class="question-form">
                    <div class="option">
                        <input type="radio" id="a1" name="question-form" value="${options[0]}" />
                        <label for="a1">${options[0]}</label>
                        <br>
                        <input type="radio" id="a2" name="question-form" value="${options[1]}" />
                        <label for="a2">${options[1]}</label>
                        <br>
                        <input type="radio" id="a3" name="question-form" value="${options[2]}" />
                        <label for="a3">${options[2]}</label>
                        <br>
                        <input type="radio" id="a4" name="question-form" value="${options[3]}" />
                        <label for="a4">${options[3]}</label>
                    </div>
                </form>
            </div>
            `)
    );
}

var mainSignature = {
    J: `class Main {\n    public static void main(String args[]) {\n        // Your code here. Use spaces for indenting and add any imports above\n    }\n} `,
    P: `# Your code here. Use spaces for indenting and add any imports above`,
    C: `int main(void){\n    // Your code here. Use spaces for indenting and add any imports above\n}`,
};
function programmingQuestion(number, question, language) {
    return $(
        $.parseHTML(`
        <div class="question-content" id="submission-container">
            <div class="question-number">Q${number}</div>
            <div class="question-content">${question}</div>
            <form class="question-form">
                <textarea type="text" class="code-editor" id="student-attempt" contenteditable="true">${mainSignature[language]}</textarea>
            </form>
        </div>

     `)
    );
}
function errorQuestion(errorMesage) {
    return $(
        $.parseHTML(`
            <div class="question-content">
                <div class="error">${errorMesage}</div>
            </div>
            `)
    );
}
