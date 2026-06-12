
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_4c8e75061075acea7dd9b09810807753 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_cac4da0447b16ff1b733d22c0eddb7dd = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_rule_sheet", ({ ["rule_type"] : "internal" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "1", ["padding"] : "9px", ["borderRadius"] : "8px", ["border"] : "1px dashed #818cf855", ["color"] : "#818cf8", ["fontSize"] : "11px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.06em", ["&:hover"] : ({ ["background"] : "#818cf80d" }) }),onClick:on_click_cac4da0447b16ff1b733d22c0eddb7dd},children)
    )
});
