variable "set_values" {
  description = "Map of values to pass to set for helm charts. Null values must be an empty string (e.g. '')"
  type        = map(any)
}
