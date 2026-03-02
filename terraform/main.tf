provider "aws" {
  region = "us-east-1"
}

# Intentional violation: SSH open to world
resource "aws_security_group" "test_sg" {
  name = "test-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "test_instance" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Environment = "dev"
    Owner       = "team"
    CostCenter  = "eng"
  }
}

# Intentional violation: Unencrypted S3 bucket