import { Body, Button, Container, Head, Heading, Html, Preview, Text } from "@react-email/components";
import * as React from "react";

export const PasswordResetEmail = () => {
  return (
    <Html>
      <Head />
      <Preview>Reset your password for {"${realmName}"}</Preview>
      <Body style={main}>
        <Container style={container}>
          <Heading style={h1}>Password Reset</Heading>
          <Text style={text}>Hello {"${user.firstName:-'User'}"},</Text>
          <Text style={text}>
            Someone requested a password reset for your account on {"${realmName}"}. 
            Click the button below to set a new password.
          </Text>
          <Button style={button} href={"${link}"}>
            Reset Password
          </Button>
        </Container>
      </Body>
    </Html>
  );
};

export default PasswordResetEmail;

const main = { backgroundColor: "#f6f9fc", fontFamily: "sans-serif" };
const container = { backgroundColor: "#ffffff", padding: "20px", border: "1px solid #eee" };
const h1 = { color: "#333", fontSize: "24px" };
const text = { color: "#555", fontSize: "16px" };
const button = { backgroundColor: "#007bff", color: "#fff", padding: "12px", borderRadius: "4px", textDecoration: "none", display: "inline-block" };
