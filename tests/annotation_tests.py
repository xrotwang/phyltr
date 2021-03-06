import csv
import fileinput
import tempfile

from phyltr.main import build_pipeline
from phyltr.plumbing.sources import ComplexNewickParser, NewickParser
from phyltr.plumbing.sinks import NewickFormatter, NullSink
from phyltr.commands.annotate import Annotate

def test_init():
    annotate = Annotate.init_from_args("-f tests/argfiles/annotation.csv -k taxon")
    # Test defaults
    assert annotate.extract == False
    assert annotate.multiple == False
    # Test file was parsed
    assert annotate.annotations

    # Test extract flag
    annotate = Annotate.init_from_args("--extract -f my_output_file.csv")
    assert annotate.extract == True
    assert annotate.multiple == False
    assert annotate.sink == NewickFormatter

    # Test that extracting to stdin disables tree output
    annotate = Annotate.init_from_args("--extract")
    assert annotate.extract == True
    assert annotate.multiple == False
    assert annotate.sink == NullSink

    # Test multiple flag
    annotate = Annotate.init_from_args("--extract --multiple")
    assert annotate.extract == True
    assert annotate.multiple == True

def test_annotate():
    lines = fileinput.input("tests/treefiles/basic.trees")
    trees = NewickParser().consume(lines)
    annotated = Annotate("tests/argfiles/annotation.csv", "taxon").consume(trees)
    for t in annotated:
        t.write(features=[])
        for l in t.get_leaves():
            assert hasattr(l, "f1")
            assert hasattr(l, "f2")
            assert hasattr(l, "f3")

def test_extract_annotations():
    lines = fileinput.input("tests/treefiles/basic.trees")
    trees = list(NewickParser().consume(lines))
    lines.close()
    with tempfile.NamedTemporaryFile(mode="r") as fp:
        for t in build_pipeline(
                """annotate -f tests/argfiles/annotation.csv -k taxon |
                 annotate --extract -f %s""" % fp.name,
                 trees):
            pass
        fp.seek(0)
        reader = csv.DictReader(fp)
        assert all((field in reader.fieldnames for field in ("f1","f2","f3")))
        assert "tree_number" not in reader.fieldnames
        for row in reader:
            if row["name"] == "A":
                assert row["f1"] == "0"
                assert row["f2"] == "1"
                assert row["f3"] == "1"

def test_extract_multiple_annotations():
    lines = fileinput.input("tests/treefiles/basic.trees")
    trees = list(NewickParser().consume(lines))
    lines.close()
    with tempfile.NamedTemporaryFile(mode="r") as fp:
        for t in build_pipeline(
                """annotate -f tests/argfiles/annotation.csv -k taxon |
                 annotate --extract --multiple -f %s""" % fp.name,
                 trees):
            pass
        fp.seek(0)
        fp.seek(0)

        reader = csv.DictReader(fp)
        assert all((field in reader.fieldnames for field in ("f1","f2","f3")))
        assert "tree_number" in reader.fieldnames
        for row in reader:
            assert int(row["tree_number"]) >= 0
            if row["name"] == "A":
                assert row["f1"] == "0"
                assert row["f2"] == "1"
                assert row["f3"] == "1"

def test_extract_with_annotations_on_root():
    lines = fileinput.input("tests/treefiles/beast_output_rate_annotations.nex")
    trees = ComplexNewickParser().consume(lines)
    with tempfile.NamedTemporaryFile(mode="r") as fp:
        for t in Annotate(extract=True, multiple=True, filename=fp.name).consume(trees):
            pass
        fp.seek(0)
        fp.seek(0)

        reader = csv.DictReader(fp)
        for row in reader:
            if row["name"] == "root":
                break
        else:
            assert False
