
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_a73f5f85e12a765cadfc258365a379dc = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_79bf22e01d0e443e6583c80d78747fce = useCallback(((_e) => (addEvents([(ReflexEvent("_call_function", ({ ["function"] : (() => null), ["callback"] : null }), ({ ["stopPropagation"] : true })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["position"] : "relative", ["zIndex"] : "1", ["width"] : "360px", ["maxWidth"] : "calc(100vw - 32px)", ["maxHeight"] : "90vh", ["overflowY"] : "auto", ["background"] : "rgba(255,255,255,0.05)", ["border"] : "1px solid rgba(255,255,255,0.14)", ["borderRadius"] : "14px", ["padding"] : "20px", ["boxShadow"] : "0 24px 64px rgba(0,0,0,0.60)" }),onClick:on_click_79bf22e01d0e443e6583c80d78747fce},children)
    )
});
