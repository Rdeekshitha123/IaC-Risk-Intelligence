provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "test_instance" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  ebs_optimized = true

  metadata_options {
    http_tokens                 = "required"
    http_endpoint               = "enabled"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted = true
  }

  tags = {
    Environment = "dev"
    Owner       = "team"
    CostCenter  = "eng"
  }
}