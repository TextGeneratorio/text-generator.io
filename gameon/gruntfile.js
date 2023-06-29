module.exports = function (grunt) {
    grunt.initConfig({
        watch: {
            less: {
                files: "static/less/*",
                tasks: ["less"]
            }
        },
        less: {
            dist: {
                files: {
                    'static/css/gameon.css': ['static/less/main.less']
                },
                options: {
                    sourceMap: true,
                    sourceMapFilename: 'static/css/gameon.css.map',
                    sourceMapBasepath: '/',
                    sourceMapRootpath: '/'
                }
            }
        }
    });
    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-watch');

    grunt.registerTask('compile', [
        'less',
        'watch'
    ]);

    grunt.registerTask('default', [
        'compile'
    ]);
};
