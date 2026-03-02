provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "test_bucket" {
  bucket = "my-test-bucket-12345"

  tags = {
    Environment = "dev"
    Owner       = "team"
    CostCenter  = "eng"
  }
}


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