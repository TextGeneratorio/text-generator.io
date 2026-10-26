from pathlib import Path


def test_same_origin_minified_scripts_do_not_advertise_missing_source_maps():
    static_root = Path("static")
    checked_scripts = [
        static_root / "libs" / "jquery-3.2.1.min.js",
        static_root / "js" / "material.min.js",
    ]

    for script_path in checked_scripts:
        source_map_path = script_path.with_name(script_path.name + ".map")
        script_text = script_path.read_text(encoding="utf-8")
        source_map_marker = "sourceMappingURL="

        if source_map_marker in script_text:
            assert source_map_path.exists(), f"{script_path} advertises missing {source_map_path}"


def test_frontend_error_logger_does_not_guess_missing_minified_source_maps():
    source = Path("static/js/frontend-error-logger.js").read_text(encoding="utf-8")

    assert "guessedSourceMapUrl" not in source
    assert ".min.js.map" not in source
    assert "sourceMapUrlFromScriptText(src, text.slice(-8000))" in source
