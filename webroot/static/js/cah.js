// WAMP session object
var sess;
var wsuri = "ws://" + window.location.hostname + ":9000";
var wamp_rpc_namespace = "http://example.com/cah#";
var wamp_event_namespace = "http://example.com/cahevent#";

$(document).ready(function () {
    cah.start();
    load_bpm_resize();
});

cah.start = function () {
    var logWrapper = function (func, name) {
        return function () {

            console.log('Function: ', name)
            $.each(arguments, function (i, arg) {
                console.log(arg);
            });
            return func.apply(this, arguments);
        }
    }

    // connect to WAMP server
    ab.connect(wsuri,
        // WAMP session was established
        function (session) {

            sess = session;
            console.log("Connected to " + wsuri);

            // subscribe to topic, providing an event handler
            $.each(cah.eventHandlers, function (name, func) {
                if (cah.debug) {
                    func = logWrapper(func, name);
                }
                sess.subscribe(wamp_event_namespace + name, func);
            });

            cah.emit = function (topic, arg1, arg2) {
                topic = wamp_rpc_namespace + topic;
                if (cah.debug) {
                    console.log("Emit: " + topic);
                    $.each(arguments, function (i, arg) {
                        console.log(arg);
                    });
                }
                if (arg2)
                    return sess.call(topic, arg1, arg2);
                else if (arg1)
                    return sess.call(topic, arg1);
                else
                    return sess.call(topic);
            };

            cah.publish = function (topic, data) {
                topic = wamp_event_namespace + topic;
                if (cah.debug) {
                    console.log("Publish: " + topic);
                    $.each(arguments, function (i, arg) {
                        console.log(arg);
                    });
                }
                return sess.publish(topic, data);
            }

            cah.emit("sync_me");

        },

        // WAMP session is gone
        function (code, reason) {
            sess = null;
            console.log("Connection lost (" + reason + ")");
        }

    );

    $('.header').on('click', '.login', function () {
        var username = $('.username').val();
        if (username.length > 0) {
            $(this).attr('disabled', '');
            cah.emit("join", username, sess.sessionid())
                .then(function (result) {
                    if (result === false) {
                        $('.login').removeAttr('disabled');
                        alert('Name already taken.');
                    }
                    else {
                        $('.login').hide();
                        cah.username = username;
                    }
                }, onError);
        }
    });

    $(".header").on('click', '.start', function () {
        cah.emit("start_game")
            .then(function (result) {
                if (result) {
                    alert(result);
                }
            });
    });

    $(".header").on('change', '.afk_checkbox', function () {
        cah.emit("update_afk", $(this).is(':checked'));
    });

    $(".hand").on('dblclick', ".white_card", function (ev) {
        if (cah.max_whites) {
            ev.preventDefault();
            return;
        }
        var $this = $(ev.target);
        var id = $this.attr('card_id');
        $this.appendTo(".play_area_whites");
        cah.emit("choose_white", +id);
        ev.preventDefault();
    });

    $('.chat_input').keydown(function (event) {
        if (!cah.username) return;
        var $this = $(this);
        if (event.keyCode == 9) {  //tab pressed
            event.preventDefault(); // stops its action
            tabComplete($this);
        }
        else {
            $this.data('tabcycle', false);
            $this.data('tabindex', 0);
            if (event.keyCode == 13) {
                var data = {
                    username:cah.username,
                    message:$this.val().replace(/\\\\([\w-]+)/g, "[](/$1)")
                };
                if (data.message) {
                    cah.publish("chat_message", data);
                    cah.eventHandlers.chat_message("chat_message", data);
                    $this.val('');
                }
            }
        }


    });

    $(".users").on('dblclick', ".kick_user", function (ev) {
        cah.emit("kick_user", cah.admin_pass, $(this).attr("username"));
    });

    cah.admin = function (password) {
        cah.admin_pass = password;
        cah.emit("sync_me");
    }
}

function onError(error, desc) {
    console.log("error: ", error, ", desc:", desc);
}

function tabComplete(elem) {
    var chat = elem.val();
    var ts = elem.data('tabcycle');
    var i = elem.data('tabindex');
    var hasTS = false;

    if (typeof ts != "undefined" && ts != false) hasTS = true;

    if (hasTS == false) {
        console.log("New Tab");
        var onlyword = new RegExp('^([^ ]*)$', 'i');
        var endword = new RegExp('([^ ]+)$', 'i');
        var m = chat.match(endword);
        if (m) {
            who = m[1];
        } else {
            return false;
        }

        var re = new RegExp('^' + who + '.*', 'i');
        var ret = []
        for (var i in cah.CHATLIST) {
            var m = cah.CHATLIST[i].match(re);
            if (m) ret.push(m[0]);
        }

        if (ret.length == 1) {
            x = chat.replace(endword, ret[0])
            if (chat.match(onlyword)) {
                x += ": "
            } else {
                x += " ";
            }
            elem.val(x);
        }
        if (ret.length > 1) {
            var ts = [];
            for (var i in ret) {
                var x = chat.replace(endword, ret[i]);
                if (chat.match(onlyword)) {
                    x += ": "
                } else {
                    x += " ";
                }
                ts.push(x);
            }
            elem.data('tabcycle', ts);
            elem.data('tabindex', 0);
            hasTS = true;
            console.log(elem.data());
        }
    }

    if (hasTS == true) {
        console.log("Cycle");
        var ts = elem.data('tabcycle');
        var i = elem.data('tabindex');
        elem.val(ts[i]);
        if (++i >= ts.length) i = 0;
        elem.data('tabindex', i);
    }

    return ret
}


var load_bpm_resize = function () {
    var $chat = $('.chat');

    var mutationObserver = this.MutationObserver || this.MozMutationObserver || this.WebKitMutationObserver;

    var mutationHandler = function (mutations) {
        for (var i = 0; i < mutations.length; ++i) {
            console.log('mutations: ', mutations, mutations[i].addedNodes && mutations[i].addedNodes.length);
            if (mutations[i].addedNodes && mutations[i].addedNodes.length) {
                var addedNodes = $(mutations[i].addedNodes);
                console.log(addedNodes);
                var emotes = addedNodes.find('.bpm-emote');
                emotes.each(function (i, emote) {
                    var $emote = $(emote);
                    if ($emote.parent().is('.bpm-wrapper')) return;
                    if ($emote.length > 0) {
                        if ($emote.height() > 150) {
                            console.log("resizing bpm emote");
                            var scale = 150 / $emote.height();
                            var innerwrap = $emote.wrap('<div class="bpm-wrapper"><div class="bpm-wrapper"></div></div>').parent();
                            var outerwrap = innerwrap.parent();
                            outerwrap.css('height', $emote.height() * scale);
                            outerwrap.css('width', $emote.width() * scale);
                            outerwrap.css('display', 'inline-block');
                            outerwrap.css('position', 'relative');
                            innerwrap.css('transform', ['scale(', scale, ', ', scale, ')'].join(''));
                            innerwrap.css('transform-origin', 'left top');
                            innerwrap.css('position', 'absolute');
                            innerwrap.css('top', '0');
                            innerwrap.css('left', '0');
                        }
                    }
                });
            }
        }
    };
    var observer = new mutationObserver(mutationHandler);
    observer.observe($chat.get(0), {
        childList:true
    });
}

