package katib_external_db_with_kubeflow

import (
	"github.com/kubeflow/manifests/tests"
	"testing"
)

func TestKustomize(t *testing.T) {
	testCase := &tests.KustomizeTestCase{
		Package: "../../../../../../apps/katib/upstream/installs/katib-external-db-with-kubeflow",
		Expected: "test_data/expected",
	}

	tests.RunTestCase(t, testCase)
}