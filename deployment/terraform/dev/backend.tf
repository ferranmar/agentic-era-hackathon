terraform {
  backend "gcs" {
    bucket = "qwiklabs-gcp-02-397d3c6120f0-terraform-state"
    prefix = "dev"
  }
}
