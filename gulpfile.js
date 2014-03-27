var gulp = require('gulp');
var less = require('gulp-less');

gulp.task('less', function() {
    return gulp.src('static/style.less')
        .pipe(less())
        .pipe(gulp.dest('static'));
});

gulp.task('watch', function() {
    gulp.watch('static/style.less', ['less']);
});

gulp.task('build', ['less']);
gulp.task('default', ['build', 'watch']);
