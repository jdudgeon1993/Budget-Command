
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_1f10c0ff65a8c4d9ecb8870ff7b4decd = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_7fd4d9d869d1dabd695905573b130fe4 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_rule_sheet", ({ ["rule_type"] : "external" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "1", ["padding"] : "9px", ["borderRadius"] : "8px", ["border"] : "1px dashed #fbbf2455", ["color"] : "#fbbf24", ["fontSize"] : "11px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.06em", ["&:hover"] : ({ ["background"] : "#fbbf240d" }) }),onClick:on_click_7fd4d9d869d1dabd695905573b130fe4},children)
    )
});
