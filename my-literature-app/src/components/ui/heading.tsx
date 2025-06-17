import { cva, type VariantProps } from "class-variance-authority";
import { HTMLAttributes } from "react";

const headingVariants = cva("font-semibold", {
  variants: {
    size: {
      sm: "text-lg",
      md: "text-xl",
      lg: "text-2xl",
      xl: "text-3xl",
      xxl: "text-4xl",
      xxxl: "text-5xl",
    },
  },
  defaultVariants: {
    size: "md",
  },
});

interface HeadingProps
  extends HTMLAttributes<HTMLHeadingElement>,
    VariantProps<typeof headingVariants> {
  as?: "h1" | "h2" | "h3" | "h4" | "h5" | "h6";
}

export function Heading({ as = "h2", size, className, children, ...props }: HeadingProps) {
  const Component = as;
  return (
    <Component className={headingVariants({ size, className })} {...props}>
      {children}
    </Component>
  );
}