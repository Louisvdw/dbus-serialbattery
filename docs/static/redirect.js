function redirect(){
    // redirect to new documentation
    if(window.location.pathname !== '/dbus-serialbattery/' && window.origin !== 'http://localhost:3000') {

        var url = window.location.href;

        url = url.replace(window.origin, 'https://mr-manuel.github.io');
        url = url.replace('/dbus-serialbattery/', '/venus-os_dbus-serialbattery_docs/');

        // redirect to new domain
        console.log(url);
        window.location.href = url;

    }
}

redirect();

window.addEventListener('popstate', function(event) {
    console.log("URL changed!", window.location.href);
    redirect();
});

window.addEventListener('hashchange', function() {
    console.log("Hash changed!", window.location.hash);
    redirect();
});
