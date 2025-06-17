import { ReactNode, HTMLAttributes } from 'react';

type TextProps = HTMLAttributes<HTMLParagraphElement> & {
  children?: ReactNode;
};

export function Text({ children, ...props }: TextProps) {
  return <p {...props}>{children}</p>;
}