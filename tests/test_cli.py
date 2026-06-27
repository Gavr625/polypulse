from polypulse.cli import build_parser, main


def test_parser_benchmark_subcommand():
    args = build_parser().parse_args(["benchmark"])
    assert args.command == "benchmark"


def test_parser_watch_requires_tokens():
    args = build_parser().parse_args(["watch", "T1", "T2"])
    assert args.command == "watch"
    assert args.tokens == ["T1", "T2"]


def test_parser_no_command_is_none():
    args = build_parser().parse_args([])
    assert args.command is None


def test_main_no_args_prints_help_and_returns_0(capsys):
    rc = main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "usage" in out.lower()
