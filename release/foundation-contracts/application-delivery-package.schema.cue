package applicationcontract

import "list"

// ApplicationZarfPackage v1alpha2 closes the source Zarf package definition
// for one exact ApplicationContract. The package is an availability transport:
// it carries immutable OCI resources and the contract as documentation, but it
// contains no deployment, action, Git, file-placement or desired-state input.

#OciDigestReference: string & =~"^[A-Za-z0-9.-]+(:[0-9]{1,5})?/[A-Za-z0-9._/-]+@sha256:[0-9a-f]{64}$"

#ApplicationZarfPackage: {
	application!: #ApplicationContract
	_expectedResources: [
		for _, artifact in application.release.artifacts {"\(artifact.repository)@\(artifact.digest)"},
	]

	package!: {
		apiVersion!: "zarf.dev/v1alpha1"
		kind!:       "ZarfPackageConfig"
		metadata!: {
			name!:         "application-\(application.metadata.name)"
			version!:      application.release.version
			description!:  "Availability-only ADASK application release; activation requires setup.yaml and GitOps."
			architecture!: "amd64"
			authors!:      #NonEmpty
			source!:       string & =~"^https://[^[:space:]]+$"
		}

		components!: [{
			name!:        "release-artifacts"
			description!: "Immutable OCI artifacts mirrored without application activation."
			required!:    true
			images!: list.MinItems(len(_expectedResources)) &
				list.MaxItems(len(_expectedResources)) &
				list.UniqueItems & [...#OciDigestReference]
		}]

		documentation!: {
			"application-contract"!: "application-contract.yaml"
		}
	}

	for _, reference in package.components[0].images {
		_declaredResource: list.Contains(_expectedResources, reference) & true
	}
}
