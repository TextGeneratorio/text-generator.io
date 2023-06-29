window.evutils = new (function () {
    "use strict";
    var self = this;

    //Modals
    self.modalHidden = true;
    $(document).ready(function () {

        var $modal = $('#modal');
        $modal.on('hide.bs.modal', function (e) {
            self.modalHidden = true;
        });

        $modal.on('show.bs.modal', function (e) {
            self.modalHidden = false;
        });
        $('.mm-hide-btn').click(function () {
            $(this).parent().hide();
        });
    });
    self.showModal = function () {
        $('#modal').modal('show');
    };
    self.hideModal = function () {
        $('#modal').modal('hide');
    };
    self.setModal = function (content) {
        $('#modal').find('.modal-body').html(content);
        self.showModal();
    };


    self.urlencode = function (name) {
        return name.replace(/\s/g, '-')
            .replace(/[\.\t\,\:;\(\)'@!\\\?#/<>&]/g, '')
            .replace(/[^\x00-\x7F]/g, "")
            .toLowerCase();
    };

    //share buttons
    $(document).on('click', '.facebook-share-btn', function () {
        FB.ui({
            method: 'share',
            href: window.location.href
        }, function (response) {
        });
    });


    self.render = function (template, opts, callback) {
        if (typeof opts === 'undefined') {
            opts = {};
        }
        opts = $.extend({
            url: window.location.href,
            urlencode: encodeURIComponent,
            window: window,
            client_side: true,
            fixtures: fixtures,
            title: document.title,
            path: document.location.pathname,
            description: $('meta[name=description]').attr('content')
        }, opts);
        return nunjucks.render(template, opts, callback);
    };


})();

nunjucks.configure({ autoescape: true });

Backbone.View.prototype.close = function () {
    this.remove();
    this.unbind();
    if (this.onClose) {
        this.onClose();
    }
};
