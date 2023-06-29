(function () {
    "use strict";
    window.APP = window.APP || {Routers: {}, Collections: {}, Models: {}, Views: {}};


    APP.Views['/'] = Backbone.View.extend({
        initialize: function (options) {
        },

        render: function () {
            var self = this;
            gameon.getUser(function (user) {
                if (user.levels_unlocked < fixtures.levels.length) {
                    var level = fixtures.levels[user.levels_unlocked];

                    APP.game = new rewordgame.Game(level);
                    APP.game.render(self.$el);
                }
            })


            return self;
        }
    });

    APP.Views['/level'] = Backbone.View.extend({
        initialize: function (options) {
            this.level = options.args[0];
        },

        render: function () {
            var self = this;

            APP.game = new rewordgame.Game(self.level);
            APP.game.render(self.$el);

            return self;
        }
    });


    APP.Views['/done-level'] = Backbone.View.extend({
        initialize: function (options) {
            this.level = options.args[0];
        },

        render: function () {
            var self = this;
            if (self.level.id >= fixtures.levels.length) {
                self.$el.html(evutils.render('static/templates/shared/donelevel.jinja2', {
                    wonGame: true
                }));

            } else {
                self.$el.html(evutils.render('static/templates/shared/donelevel.jinja2'));
                window.setTimeout(function () {
                    APP.router.level(fixtures.levels[self.level.id + 1])
                }, 1000);
            }
            return self
        }
    });

    APP.Views['/contact'] = Backbone.View.extend({
        initialize: function (options) {
        },

        render: function () {
            this.$el.html(evutils.render('static/templates/shared/contact.jinja2'));
            return this;
        }
    });

    APP.Views['/about'] = Backbone.View.extend({
        initialize: function (options) {
        },

        render: function () {
            this.$el.html(evutils.render('static/templates/shared/about.jinja2'));
            return this;
        }
    });
    APP.Views['/terms'] = Backbone.View.extend({
        initialize: function (options) {
        },

        render: function () {
            this.$el.html(evutils.render('static/templates/shared/terms.jinja2'));
            return this;
        }
    });
    APP.Views['/privacy'] = Backbone.View.extend({
        initialize: function (options) {
        },

        render: function () {
            this.$el.html(evutils.render('static/templates/shared/privacy.jinja2'));
            return this;
        }
    });


    APP.Views.Header = Backbone.View.extend({
        initialize: function (options) {
            this.path = options.path;
        },

        render: function () {
            var self = this;
            gameon.getUser(function (user) {
                self.$el.html(evutils.render('static/templates/shared/header.jinja2', {'path': self.path, 'user': user}));
            });

            return self;
        }
    });

    APP.Views.Footer = Backbone.View.extend({
        initialize: function (options) {
            this.path = options.path;
        },

        render: function () {
            this.$el.html(evutils.render('static/templates/shared/footer.jinja2', {'path': this.path}));
            return this;
        }
    });

}());
