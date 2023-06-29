module.exports = function (grunt) {
    grunt.initConfig({
        nunjucks: {
            precompile: {
                baseDir: 'templates/shared/',
                src: ['templates/shared/*', '!templates/shared/about.jinja2', '!templates/shared/terms.jinja2', '!templates/shared/privacy.jinja2'],
                dest: 'static/js/templates.js',
                options: {
//                    env: require('./nunjucks-environment'),
                    name: function (filename) {
                        return filename;
//                        return filename.substring(filename.lastIndexOf("/") + 1, filename.lastIndexOf("."));
                    }
                }
            }
        },
        watch: {
            nunjucks: {
                files: ['templates/shared/*', '!templates/shared/about.jinja2', '!templates/shared/about.jinja2', '!templates/shared/terms.jinja2', '!templates/shared/privacy.jinja2'],
                tasks: ['nunjucks']
            },
            less: {
                files: "static/less/*",
                tasks: ["less"]
            }
        },
        less: {
            dist: {
                files: {
                    'static/css/style.css': ['static/less/main.less']
                },
                options: {
                    sourceMap: true,
                    sourceMapFilename: 'static/css/style.css.map',
                    sourceMapBasepath: '/',
                    sourceMapRootpath: '/'
                }
            }
        }
    });
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-nunjucks');

    grunt.registerTask('compile', [
        'nunjucks',
        'less',
        'watch'
    ]);

    grunt.registerTask('default', [
        'compile'
    ]);
};
