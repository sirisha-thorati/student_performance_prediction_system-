function togglePassword() {
    var password = document.getElementById("password");
    var eye = document.getElementById("eye");

    if (password.type === "password") {
        password.type = "text";
        eye.classList.add("fa-eye");
        eye.classList.remove("fa-eye-slash");
    } else {
        password.type = "password";
        eye.classList.add("fa-eye-slash");
        eye.classList.remove("fa-eye");
    }
}

