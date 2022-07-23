package rds_s3

import (
	"github.com/kubeflow/manifests/tests"
	"testing"
)

func TestKustomize(t *testing.T) {
	testCase := &tests.KustomizeTestCase{
		Package: "../../../../../docs/deployment/rds-s3",
		Expected: "test_data/expected",
	}

	tests.RunTestCase(t, testCase)
}