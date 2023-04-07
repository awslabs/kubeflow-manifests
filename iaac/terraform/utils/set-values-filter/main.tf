locals {
  set_values = [for k, v in var.set_values : { name = k, value = v } if v != null]
}
